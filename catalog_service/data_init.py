# catalog_service/data_init.py
from model import Book, Exemplar
from db import SessionLocal
from sqlalchemy.exc import SQLAlchemyError

SAMPLE_TITLES = [
    "Dom Quixote","Os Lusíadas","Mensagem","A Cidade e as Serras","O Primo Basílio",
    "Ensaio sobre a Cegueira","O Ano da Morte de Ricardo Reis","Peregrinação","A Hora da Estrela",
    "Vidas Secas","Memorial do Convento","Livro do Desassossego","A Maior Flor do Mundo",
    "A Relíquia","A Jangada de Pedra","Os Maias","Os Maias II","O Crime do Padre Amaro",
    "A Alma do Mundo","Contos"
]

def seed_data():
    db = SessionLocal()
    try:
        exists = db.query(Book).first()
        if exists:
            print("catalog_service: books already exist, skipping seed.")
            return

        for i, title in enumerate(SAMPLE_TITLES[:20], start=1):
            book = Book(
                title=title,
                authors="Autor Exemplo",
                isbn=f"ISBN-EX-{1000+i}",
                publisher="Editor Exemplo",
                year=1900 + (i % 120),
                description=f"Descrição de {title}"
            )
            db.add(book)
            db.flush()  # para obter book.id

            exemplar = Exemplar(
                book_id=book.id,
                barcode=f"BC-{10000+i}",
                available=True,
                location=f"Estante {chr(65 + (i % 6))}{(i%10)+1}",
                condition="good"
            )
            db.add(exemplar)

        db.commit()
        print("catalog_service: seeded 20 books + exemplars.")
    except SQLAlchemyError as e:
        db.rollback()
        print("catalog_service: error seeding books:", e)
    finally:
        db.close()
