from pymongo import MongoClient
import gridfs
import os

client = MongoClient("mongodb://localhost:27017/")
db = client["clothes"]

fs = gridfs.GridFS(db)

collections = {
    "dresses": ["C:\\Users\\ofeka\\Downloads\\Dresses\\images"],
    "skirts": ["C:\\Users\\ofeka\\oneDrive\\My Drive\\finalProject\\BeautifulSoup\\Skirts\\images"],
    "upperwear": ["C:\\Users\\ofeka\\oneDrive\\Drive\\finalProject\\BeautifulSoup\\Tops\\images","C:\\Users\\ofeka\\oneDrive\\Drive\\finalProject\\BeautifulSoup\\Shirts\\images","C:\\Users\\ofeka\\oneDrive\\Drive\\finalProject\\BeautifulSoup\\Knitwear\\images"],
    "pants": ["C:\\Users\\ofeka\\oneDrive\\Drive\\finalProject\\BeautifulSoup\\Trousers\\images","C:\\Users\\ofeka\\oneDrive\\Drive\\finalProject\\BeautifulSoup\\Shorts\\images","C:\\Users\\ofeka\\oneDrive\\Drive\\finalProject\\BeautifulSoup\\Leggings\\images","C:\\Users\\ofeka\\oneDrive\\Drive\\finalProject\\BeautifulSoup\\Jeans\\images"],
}

for collection_name, folder_paths in collections.items():
    print(f"Uploading images to {collection_name}...")

    for folder_path in folder_paths:
        if not os.path.exists(folder_path):
            print(f"❌ Folder not found: {folder_path}")
            continue

        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, "rb") as image_file:
                file_id = fs.put(image_file, filename=filename, collection=collection_name)
                print(f"✅ Uploaded {filename} from {folder_path} to {collection_name} (ID: {file_id})")

print("🎉 All images uploaded successfully!")