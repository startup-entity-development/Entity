from datetime import datetime
import hashlib
import json
import os
import time
from graphene_sqlalchemy import SQLAlchemyObjectType
from models.model_account import ModelAccount
from models.model_news import ModelNews
from models.model_news_views import ModelNewsViews
from models.model_role import ModelRole
import graphene
from general_functions import utils
from models.base import db_session
from graphql_auth import (
    mutation_jwt_refresh_token_required, get_jwt_identity,
    create_access_token, create_refresh_token, mutation_header_jwt_required, get_jwt_claims
)


class News(SQLAlchemyObjectType):
    """News node."""

    class Meta:
        model = ModelNews
        interfaces = (graphene.relay.Node,)

class ViewsNews(SQLAlchemyObjectType):
    """ViewsNews node."""

    class Meta:
        model = ModelNewsViews
        interfaces = (graphene.relay.Node,)


class NewsAttributeCreate(graphene.InputObjectType):
    title = graphene.String(description="Title of the news", required=True)
    body = graphene.String(description="Body of the news")
    image_url = graphene.String(description="url of the image")


class NewsAttributeUpdate(graphene.InputObjectType):
    id = graphene.ID(description="Id of the News.", required=True)
    title = graphene.String(description="Title of the news")
    body = graphene.String(description="Body of the news")
    image_url = graphene.String(description="url of the image")


class NewsAttributeDelete(graphene.InputObjectType):
    id = graphene.ID(description="Id of the News.", required=True)


class NewsViewsAttribute(graphene.InputObjectType):
    news_list = graphene.List(
        graphene.ID, description="Id of the News.", required=True)
    account_id = graphene.String(
        description="Account that saw/partially saw the news", required=True)


class CreateNews(graphene.Mutation):
    ''' Mutation to create a news! '''

    news = graphene.Field(
        lambda: News, description="News node create by this mutation")

    class Arguments:
        input = NewsAttributeCreate(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):

        # Who is trying to update the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account: ModelAccount = db_session.query(ModelAccount).get(id_account_token)
        if account is None:
            raise Exception(f"Account trying to create the news not found")
        perms = ['news.add']
        utils.evaluate_permissions(perms, account)
        data = utils.input_to_dictionary(input)

        
        data['account_id'] = account.id
        data["created"] = str(int(time.time()))
        news = ModelNews(**data)
        db_session.add(news)
        try:
            db_session.flush()
            db_session.refresh(news)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            db_session.close()
            raise Exception(
                f"Error creating news for {data['title']} error: {e.__cause__}")
        return CreateNews(news=news)


class UpdateNews(graphene.Mutation):
    """Update a News."""
    news = graphene.Field(
        lambda: News, description="News node created by this mutation")

    class Arguments:
        input = NewsAttributeUpdate(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):

        # Who is trying to update the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['news.update']
        utils.evaluate_permissions(perms, account)
        data = utils.input_to_dictionary(input)

        # Delete old image if the new one is different
        news:ModelNews = db_session.query(ModelNews).get(data['id'])
        if (data["image_url"] != news.image_url):
            delete_image(news.image_url)

        if not news:
            db_session.rollback()
            db_session.close()
            raise Exception('|$NE1002 - News Not found')
        try:
            news = db_session.query(ModelNews).filter_by(id=data['id'])
            news.update(input)
        except Exception as e:
            raise Exception(f'Error in update: {e.__cause__}')
        db_session.commit()

        news = db_session.query(ModelNews).filter_by(id=data['id']).first()
        db_session.refresh(news)
        return UpdateNews(news=news)


class DeleteNews(graphene.Mutation):
    """ Delete News"""
    is_deleted = graphene.Boolean(
        description="if the News is deleted return true")

    class Arguments:
        input = NewsAttributeDelete(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        is_deleted: bool = False

        # Who is trying to delete the News?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['news.delete']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        news: ModelNews = db_session.query(ModelNews).filter_by(id=data['id']).first()
        if not news:
            db_session.rollback()
            db_session.close()
            raise Exception('|$NE1001 - News Not found')
        try:
            delete_image(news.image_url)
            db_session.delete(news)
            db_session.commit()
        except Exception as e:
            raise Exception(
                f"Error to delete news {e.__cause__}")
        is_deleted = True
        db_session.close()
        return DeleteNews(is_deleted=is_deleted)


class ViewsOfNews(graphene.Mutation):
    """ Mark the News as viewed"""
    was_saw = graphene.Boolean(
        description="if the News was saw return true")

    class Arguments:
        input = NewsViewsAttribute(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        was_saw: bool = False

        # Who is trying to delete the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['newsviews.update']
        utils.evaluate_permissions(perms, account)

        data: dict = utils.input_to_dictionary(input)

        for news_id in data["news_list"]:

            # Does the news exists? If it doesn't we just not add any view for it. No exception needed
            news = db_session.query(ModelNews).filter_by(id=news_id).first()
            if not news:
                pass

            # If the news was already saw, then we update the datetime. Otherwise we create a view
            viewed_news: ModelNewsViews = news_was_already_saw(
                news_id, data["account_id"])
            if viewed_news:
                update_view_datetime_news(news_id, data)
                was_saw = True
            else:
                # Create model
                views_news = ModelNewsViews(
                    viewed_at=str(int(time.time())),
                    partially_viewed_at=None,
                    news_id=news_id,
                    account_id=data["account_id"]
                )

                # Database operations
                db_session.add(views_news)
                try:
                    db_session.flush()
                    db_session.refresh(views_news)
                    db_session.commit()
                except Exception as e:
                    db_session.rollback()
                    db_session.close()
                    raise Exception(
                        f"Error creating views of news for news {data['news_list']} error: {e.__cause__}")

        was_saw = True
        db_session.close()
        return ViewsOfNews(was_saw=was_saw)


def news_was_already_saw(news_id: str, account_id: str) -> ModelNewsViews:
    views_new: ModelNewsViews = db_session.query(ModelNewsViews).filter_by(
        news_id=news_id, account_id=account_id).first()
    return views_new


def update_view_datetime_news(news_id: str, data: dict) -> None:
    views_new: ModelNewsViews = db_session.query(ModelNewsViews).filter_by(
        news_id=news_id, account_id=data["account_id"])
    views_new.update({"viewed_at": str(int(time.time())),
                      "partially_viewed_at": None})
    db_session.commit()


def delete_image(image_url:str) -> None:
    if image_url != None:
        shorted_path = image_url.find('/images_folder/')
        if (os.path.exists(f'/app{image_url[shorted_path:]}')):
            os.unlink(f'/app{image_url[shorted_path:]}')

