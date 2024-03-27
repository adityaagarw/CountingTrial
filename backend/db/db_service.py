from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

class DBService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.init_db()
        return cls._instance

    def init_db(self):
        self.engine = create_engine('postgresql://avian-admin:avian-password@localhost:5432/avian-db')
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def get_session(self):
        return self.Session()

    def dispatch(self, model, action, *args, **kwargs):
        session = self.get_session()
        try:
            if action == 'add':
                session.add(*args)
            elif action == 'add_all':
                session.add_all(*args)
            elif action == 'delete':
                session.delete(model(*args, **kwargs))
            elif action == 'query':
                return session.query(model).filter(*args).all()
            elif action == 'query_one':
                return session.query(model).filter(*args).first()
            elif action == 'query_count':
                return session.query(model).filter(*args).count()
            else:
                raise ValueError(f"Invalid action: {action}")
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()