import os
import uuid
from shutil import copyfileobj

from fastapi import FastAPI, File, UploadFile, Depends, Form
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from database import SessionLocal, Category, Product

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", response_class=HTMLResponse)
def root():
    # 返回 frontend/index.html 文件
    file_path = os.path.join(os.getcwd(), 'frontend', 'index.html')
    with open(file_path, 'r') as file:
        content = file.read()
    return content


@app.get("/admin/categories", response_class=HTMLResponse)
def category_form():
    file_path = os.path.join(os.getcwd(), 'frontend', 'category_form.html')
    with open(file_path, 'r') as file:
        content = file.read()
    return content


@app.get("/admin/products", response_class=HTMLResponse)
def product_form():
    file_path = os.path.join(os.getcwd(), 'frontend', 'product_form.html')
    with open(file_path, 'r') as file:
        content = file.read()
    return content


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/categories/")
def create_category(name: str = Form(...), db: Session = Depends(get_db)):
    db_category = Category(name=name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/api/categories/")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@app.post("/api/products/")
async def create_product(
        catid: int = Form(...),
        name: str = Form(...),
        price: float = Form(...),
        description: str = Form(...),
        image: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    # 创建存储上传图片的目录，如果目录不存在
    images_dir = os.path.join("frontend", "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # Store the uploaded file with a unique name
    file_ext = os.path.splitext(image.filename)[1]
    unique_filename = str(uuid.uuid4()) + file_ext
    file_path = os.path.join("frontend", "images", unique_filename)

    with open(file_path, "wb") as buffer:
        copyfileobj(image.file, buffer)

    # Create the product record in the database
    db_product = Product(catid=catid, name=name, price=price, description=description, image=unique_filename)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/api/products/category/{catid}")
def get_products_by_category(catid: int, db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.catid == catid).all()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
