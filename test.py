import requests
import numpy as np

vector = np.load("finto/data/intermediate/vectors.npy")[0].tolist()

res = requests.post("http://localhost:6333/collections/my-collection/points/search", json={
    "vector": vector,
    "vector_name": "all-MiniLM-L6-v2",
    "limit": 1
})
print(res.json())