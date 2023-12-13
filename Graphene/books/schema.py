import graphene
from graphene_django import DjangoObjectType
from .models import Books, Author


class AuthorType(DjangoObjectType):
    class Meta:
        model = Author


class BooksType(DjangoObjectType):
    class Meta:
        model = Books


class Query(graphene.ObjectType):
    books = graphene.List(BooksType)
    author_books_by_name = graphene.List(AuthorType, name=graphene.String())

    def resolve_books(self, request_info):
        # Access the requested fields from the 'info' object
        requested_fields = request_info.field_nodes[0].selection_set.selections

        # Extract the names of the requested fields
        requested_field_names = [field.name.value for field in requested_fields]

        if "author" in requested_field_names:
            books_list = Books.objects.select_related("author")

        else:
            books_list = Books.objects.all()

        print(books_list.query)

        return books_list

    def resolve_author_books_by_name(self, request_info, name):
        authors = Author.objects.filter(name=name).prefetch_related("books_set")
        return authors


schema = graphene.Schema(query=Query)
