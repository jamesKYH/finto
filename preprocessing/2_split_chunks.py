from pathlib import Path
import re
import json

# 입력 및 출력 파일 경로 수정
INPUT_FILE = Path("data/raw/sample.txt")
OUTPUT_FILE = Path("finto/data/intermediate/structured_chunks.json")

def identify_chapter(text):
    """법령 텍스트에서 장(章) 정보를 식별합니다."""
    chapter_info = {
        "chapter_no": None,
        "chapter_title": None
    }
    
    # '제n장 제목' 패턴 찾기
    chapter_match = re.search(r"제(\d+)장\s+(.+?)\s*(?:<개정|$|\n)", text)
    if chapter_match:
        chapter_info["chapter_no"] = f"제{chapter_match.group(1)}장"
        chapter_info["chapter_title"] = chapter_match.group(2).strip()
    
    return chapter_info

def split_legal_text(text):
    """법령 텍스트를 장, 조, 항 등의 단위로 분할합니다."""
    # 텍스트에서 장(章) 경계 식별
    chapter_boundaries = [m.start() for m in re.finditer(r"\s+제\d+장\s+.+?(?:<개정|$|\n)", text)]
    
    # 기본 분할 패턴 (조문, 부칙, 별표) - '제1조' 또는 '1조' 두 가지 형식 모두 매칭
    section_pattern = r"(?=\s+(?:제)?\d+조\s*\(.+?\))|(?=\s*부\s*칙\s*(?:<.+?>)?)|(?=\s*\[별표\s*\])"
    
    # 장별로 조문 분할
    current_chapter = {"chapter_no": None, "chapter_title": None}
    result_sections = []
    
    if not chapter_boundaries:  # 장 구분이 없는 경우
        # 기존 방식으로 조문 단위 분할
        sections = re.split(section_pattern, text, flags=re.MULTILINE)
        for section in sections:
            if section and section.strip():  # None 체크 추가
                result_sections.append({
                    "text": section.strip(),
                    "chapter": current_chapter.copy()
                })
    else:
        # 장 단위로 먼저 분할 후 조문 분할
        for i, start_pos in enumerate(chapter_boundaries):
            # 장의 끝 위치 결정
            end_pos = chapter_boundaries[i+1] if i+1 < len(chapter_boundaries) else len(text)
            chapter_text = text[start_pos:end_pos]
            
            # 현재 장 정보 저장
            current_chapter = identify_chapter(chapter_text)
            
            # 장 내 조문 분할
            chapter_sections = re.split(section_pattern, chapter_text, flags=re.MULTILINE)
            for section in chapter_sections:
                if section and section.strip():  # None 체크 추가
                    result_sections.append({
                        "text": section.strip(),
                        "chapter": current_chapter.copy()
                    })
    
    # 부가 정보 추출 (법령명, 시행일 등)
    header_info = extract_header_info(text)
    for section in result_sections:
        section["header_info"] = header_info
    
    return result_sections

def extract_header_info(text):
    """법령 텍스트 상단에서 법령명, 시행일 등 기본 정보를 추출합니다."""
    header_info = {}
    
    # 법령명 추출
    first_line = text.split('\n')[0].strip()
    if first_line and not first_line.startswith('제'):
        header_info["law_name"] = first_line
    
    # 시행일 및 공포번호 추출
    sihaeng_match = re.search(r"\[시행\s+(.+?)\]\s*\[(.+?)\]", text)
    if sihaeng_match:
        header_info["effective_date"] = sihaeng_match.group(1).strip()
        header_info["publication_info"] = sihaeng_match.group(2).strip()
    
    # 소관부처 추출
    ministry_match = re.search(r"([^\[\]\n]+)\([^\(\)\n]+\),\s*\d{2,3}-\d{3,4}-\d{4}", text)
    if ministry_match:
        header_info["ministry"] = ministry_match.group(1).strip()
    
    return header_info

def extract_article_info(text):
    """조문 번호와 제목을 추출합니다. '제1조' 또는 '1조' 두 형식 모두 지원합니다."""
    article_info = {
        "article_no": None,
        "article_title": None
    }
    
    # '제n조' 또는 'n조' 형식 모두 매칭
    article_match = re.search(r"(?:제)?(\d+)조(?:\s*\((.+?)\))", text)
    if article_match:
        article_info["article_no"] = f"제{article_match.group(1)}조"
        article_info["article_title"] = article_match.group(2) if article_match.group(2) else ""
    
    return article_info

def split_section_details(section_text):
    """조문 내부의 항, 호, 목 등을 분리합니다."""
    # 먼저 조문 번호와 제목 정보 추출
    article_info = extract_article_info(section_text)
    
    # 조문 내 항 분리 (①, ②, ... 기준)
    items = re.split(r"(?=\s*[①-⑳]\s+)", section_text)
    
    if len(items) <= 1:  # 항 구분이 없는 경우
        return [{"text": section_text, "article_info": article_info}]
    
    # 결과 저장할 리스트
    result = []
    
    # 첫 번째 항은 조문 제목과 내용을 포함
    result.append({"text": items[0].strip(), "article_info": article_info})
    
    # 나머지 항은 개별적으로 처리하면서 상위 조문 정보 유지
    for item in items[1:]:
        if item.strip():
            # 항 번호 추출
            item_match = re.search(r"^([①-⑳])\s+", item)
            item_no = item_match.group(1) if item_match else None
            
            # 항 번호가 있는 경우 메타데이터에 추가
            item_article_info = article_info.copy()
            if item_no:
                item_article_info["item_no"] = item_no
            
            result.append({"text": item.strip(), "article_info": item_article_info})
    
    return result

def extract_article_metadata(text, chapter_info=None, header_info=None, article_info=None):
    """텍스트에서 메타데이터를 추출합니다."""
    metadata = {}
    
    # 기본 정보 설정
    if header_info:
        metadata.update({
            "law_name": header_info.get("law_name", ""),
            "effective_date": header_info.get("effective_date", ""),
            "publication_info": header_info.get("publication_info", ""),
            "ministry": header_info.get("ministry", "")
        })
    
    # 장 정보 추가
    if chapter_info and chapter_info.get("chapter_no"):
        metadata["chapter_no"] = chapter_info.get("chapter_no")
        metadata["chapter_title"] = chapter_info.get("chapter_title")
    
    # 상위 조문 정보가 있으면 추가
    if article_info:
        if article_info.get("article_no"):
            metadata["article_no"] = article_info.get("article_no")
            metadata["article_title"] = article_info.get("article_title", "")
        
        # 항 번호가 있으면 추가
        if article_info.get("item_no"):
            metadata["item_no"] = article_info.get("item_no")
            metadata["detail_type"] = "항"
    
    # 현재 텍스트에서 조문 정보 재추출 (우선순위: 텍스트 > 상위 정보)
    article_match = re.search(r"(?:제)?(\d+)조(?:\s*\((.+?)\))", text)
    if article_match:
        # 텍스트 자체가 조문이면 정보 업데이트
        metadata["article_no"] = f"제{article_match.group(1)}조"
        metadata["article_title"] = article_match.group(2) if article_match.group(2) else ""
        metadata["section_type"] = "조문"
        
        # 항 번호 추출
        item_match = re.search(r"([①-⑳])\s+", text)
        if item_match:
            metadata["item_no"] = item_match.group(1)
            metadata["detail_type"] = "항"
            
            # 호 번호 추출 (1., 2., ...)
            subitem_match = re.search(r"\s+(\d+\.)\s+", text)
            if subitem_match:
                metadata["subitem_no"] = subitem_match.group(1)
                metadata["subdetail_type"] = "호"
        
    elif "부칙" in text:
        metadata["section_type"] = "부칙"
        # 부칙 번호 추출
        addendum_match = re.search(r"<(.+?)\s+제(\d+)호", text)
        if addendum_match:
            metadata["addendum_type"] = addendum_match.group(1)
            metadata["addendum_no"] = addendum_match.group(2)
            
    elif "별표" in text or "과태료의 부과기준" in text:
        metadata["section_type"] = "별표"
        table_match = re.search(r"\[별표\s*(\d*)\]\s*(.+)", text)
        if table_match:
            metadata["table_no"] = table_match.group(1) if table_match.group(1) else "1"
            metadata["table_title"] = table_match.group(2) if table_match.group(2) else ""
    else:
        # 조문 정보가 없고 항 번호가 있는 경우 (조문의 일부분)
        item_match = re.search(r"([①-⑳])\s+", text)
        if item_match and article_info and article_info.get("article_no"):
            metadata["item_no"] = item_match.group(1)
            metadata["detail_type"] = "항"
            metadata["section_type"] = "조문"
    else:
        metadata["section_type"] = "기타"

    # 개정 정보 추출
    amendment_match = re.search(r"<개정\s+(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})>", text)
    if amendment_match:
        metadata["amendment_date"] = amendment_match.group(1)
    
    # 전문개정 정보 추출
    full_amendment_match = re.search(r"\[전문개정\s+(\d{4}\.\s*\d{1,2}\.\s*\d{1,2})\]", text)
    if full_amendment_match:
        metadata["full_amendment_date"] = full_amendment_match.group(1)

    return metadata

# 메인 처리 부분
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    raw_text = f.read()

# 법령 텍스트 분할
sections = split_legal_text(raw_text)

# 추가 분할 및 메타데이터 추출
structured_chunks = []
for i, section in enumerate(sections):
    # 각 섹션 내부의 항/호/목 분할
    subsections = split_section_details(section["text"])
    
    for j, subsection_data in enumerate(subsections):
        subsection = subsection_data["text"]
        article_info = subsection_data["article_info"]
        
        # 메타데이터 추출
        metadata = extract_article_metadata(
            subsection, 
            chapter_info=section.get("chapter"), 
            header_info=section.get("header_info"),
            article_info=article_info
        )
        
        # 정제된 콘텐츠 생성
        cleaned_content = re.sub(r'\s+', ' ', subsection).strip()
        cleaned_content = re.sub(r'조문체계도버튼연혁', '', cleaned_content)
        
        # 고유 ID 생성 (장-조-항 형식)
        chunk_id = f"{i}-{j}"  # 기본 ID
        
        if "chapter_no" in metadata and "article_no" in metadata:
            # 장 번호 추출
            chapter_match = re.search(r"제(\d+)장", metadata["chapter_no"])
            chapter_num = chapter_match.group(1) if chapter_match else ""
            
            # 조 번호 추출
            article_match = re.search(r"제(\d+)조", metadata["article_no"])
            article_num = article_match.group(1) if article_match else ""
            
            # 표준 ID 형식: 장-조 또는 장-조-항
            if chapter_num and article_num:
                chunk_id = f"{chapter_num}-{article_num}"
                if "item_no" in metadata:
                    chunk_id += f"-{metadata['item_no']}"
        
    structured_chunks.append({
            "id": chunk_id,
            "content": subsection.strip(),
            "cleaned_content": cleaned_content,
        "metadata": metadata
    })

# 중복 확인 (동일한 ID를 가진 항목 처리)
id_count = {}
for chunk in structured_chunks:
    chunk_id = chunk["id"]
    if chunk_id in id_count:
        id_count[chunk_id] += 1
        # 중복 ID인 경우 접미사 추가
        chunk["id"] = f"{chunk_id}-{id_count[chunk_id]}"
    else:
        id_count[chunk_id] = 1

# 결과 저장
output_dir = OUTPUT_FILE.parent
output_dir.mkdir(parents=True, exist_ok=True)  # 디렉토리가 없으면 생성

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(structured_chunks, f, ensure_ascii=False, indent=2)

print(f"✅ 법령 청크 분할 및 메타데이터 저장 완료: {len(structured_chunks)}개 → {OUTPUT_FILE}")
