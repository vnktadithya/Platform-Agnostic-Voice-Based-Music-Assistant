import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.configurations.database import Base

class SystemUser(Base):
    __tablename__ = "system_users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    platform_accounts = relationship("PlatformAccount", back_populates="owner")

class PlatformAccount(Base):
    __tablename__ = "platform_accounts"
    id = Column(Integer, primary_key=True, index=True)
    system_user_id = Column(Integer, ForeignKey("system_users.id"))
    platform_name = Column(String, index=True)
    platform_user_id = Column(String, index=True)
    refresh_token = Column(String, nullable=True)
    meta_data = Column(JSON, nullable=True)
    owner = relationship("SystemUser", back_populates="platform_accounts")
    playlists = relationship("UserPlaylist", back_populates="account")
    liked_songs = relationship("UserLikedSong", back_populates="account")
    last_synced = Column(DateTime, default=None, nullable=True)

class UserPlaylist(Base):
    __tablename__ = "user_playlists"
    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"))
    playlist_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    meta_data = Column(JSON, nullable=True)
    last_synced = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    account = relationship("PlatformAccount", back_populates="playlists")

class UserLikedSong(Base):
    __tablename__ = "user_liked_songs"
    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"))
    track_uri = Column(String, unique=True, index=True)
    meta_data = Column(JSON, nullable=True)
    last_synced = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    account = relationship("PlatformAccount", back_populates="liked_songs")

class SearchCache(Base):
    __tablename__ = "search_cache"
    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"))
    normalized_query = Column(String, index=True)
    track_uri = Column(String, index=True)
    meta_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))

class InteractionLog(Base):
    __tablename__ = "interaction_logs"
    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id"))
    session_id = Column(String, index=True)
    user_input = Column(String)
    llm_response = Column(JSON)
    final_action = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))