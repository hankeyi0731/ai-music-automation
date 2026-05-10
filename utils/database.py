from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URI

Base = declarative_base()

class HotspotRecord(Base):
    """热点记录"""
    __tablename__ = 'hotspots'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50))
    rank = Column(Integer)
    title = Column(String(200))
    hot_value = Column(String(50))
    type = Column(String(20))
    crawl_time = Column(DateTime, default=datetime.now)

class AnalysisRecord(Base):
    """分析记录"""
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    hotspot_id = Column(Integer)
    surface_fact = Column(Text)
    emotion = Column(Text)
    core_meaning = Column(Text)
    music_fit = Column(Text)
    target_audience = Column(Text)
    content_derivation = Column(Text)
    keywords = Column(Text)
    structure = Column(Text)
    analysis_time = Column(DateTime, default=datetime.now)

class PromptRecord(Base):
    """Prompt记录"""
    __tablename__ = 'prompts'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer)
    prompt = Column(Text)
    song_type = Column(String(20))
    tool = Column(String(50))
    platforms = Column(Text)
    emotion_type = Column(String(20))
    genre = Column(String(50))
    bpm = Column(String(20))
    create_time = Column(DateTime, default=datetime.now)

class AudioRecord(Base):
    """音频记录"""
    __tablename__ = 'audios'
    
    id = Column(Integer, primary_key=True)
    prompt_id = Column(Integer)
    filepath = Column(String(500))
    quality_info = Column(String(200))
    success = Column(Integer)
    create_time = Column(DateTime, default=datetime.now)

class PublishRecord(Base):
    """发布记录"""
    __tablename__ = 'publishes'
    
    id = Column(Integer, primary_key=True)
    audio_id = Column(Integer)
    title = Column(String(200))
    platform = Column(String(50))
    audio_file = Column(String(500))
    publish_time = Column(DateTime)
    song_type = Column(String(20))

class DataRecord(Base):
    """数据记录"""
    __tablename__ = 'data_records'
    
    id = Column(Integer, primary_key=True)
    publish_id = Column(Integer)
    plays = Column(Integer)
    completion_rate = Column(Float)
    likes = Column(Integer)
    favorites = Column(Integer)
    shares = Column(Integer)
    crawl_time = Column(DateTime)

class MemoryRecord(Base):
    """记忆记录"""
    __tablename__ = 'memory'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100))
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.now)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URI)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def add_hotspot(self, hotspot):
        """添加热点记录"""
        session = self.Session()
        record = HotspotRecord(
            platform=hotspot.get('platform'),
            rank=hotspot.get('rank'),
            title=hotspot.get('title'),
            hot_value=hotspot.get('hot_value'),
            type=hotspot.get('type')
        )
        session.add(record)
        session.commit()
        session.close()
        return record.id
    
    def add_analysis(self, hotspot_id, analysis):
        """添加分析记录"""
        import json
        session = self.Session()
        record = AnalysisRecord(
            hotspot_id=hotspot_id,
            surface_fact=json.dumps(analysis.get('surface_fact'), ensure_ascii=False),
            emotion=json.dumps(analysis.get('emotion'), ensure_ascii=False),
            core_meaning=json.dumps(analysis.get('core_meaning'), ensure_ascii=False),
            music_fit=json.dumps(analysis.get('music_fit'), ensure_ascii=False),
            target_audience=json.dumps(analysis.get('target_audience'), ensure_ascii=False),
            content_derivation=json.dumps(analysis.get('content_derivation'), ensure_ascii=False),
            keywords=json.dumps(analysis.get('keywords'), ensure_ascii=False),
            structure=json.dumps(analysis.get('structure'), ensure_ascii=False)
        )
        session.add(record)
        session.commit()
        session.close()
        return record.id
    
    def add_prompt(self, analysis_id, prompt_data):
        """添加Prompt记录"""
        import json
        session = self.Session()
        record = PromptRecord(
            analysis_id=analysis_id,
            prompt=prompt_data.get('prompt'),
            song_type=prompt_data.get('song_type'),
            tool=prompt_data.get('tool'),
            platforms=json.dumps(prompt_data.get('platforms'), ensure_ascii=False),
            emotion_type=prompt_data.get('emotion_type'),
            genre=prompt_data.get('genre'),
            bpm=prompt_data.get('bpm')
        )
        session.add(record)
        session.commit()
        session.close()
        return record.id
    
    def add_audio(self, prompt_id, audio_result):
        """添加音频记录"""
        session = self.Session()
        record = AudioRecord(
            prompt_id=prompt_id,
            filepath=audio_result.get('filepath'),
            quality_info=audio_result.get('quality_info'),
            success=1 if audio_result.get('success') else 0
        )
        session.add(record)
        session.commit()
        session.close()
        return record.id
    
    def add_publish(self, audio_id, publish_result):
        """添加发布记录"""
        from datetime import datetime
        session = self.Session()
        record = PublishRecord(
            audio_id=audio_id,
            title=publish_result.get('title'),
            platform=publish_result.get('platform'),
            audio_file=publish_result.get('audio_file'),
            publish_time=datetime.strptime(publish_result.get('publish_time'), '%Y-%m-%d %H:%M:%S'),
            song_type=publish_result.get('song_type')
        )
        session.add(record)
        session.commit()
        session.close()
        return record.id
    
    def add_data_record(self, publish_id, data):
        """添加数据记录"""
        from datetime import datetime
        session = self.Session()
        record = DataRecord(
            publish_id=publish_id,
            plays=data.get('plays'),
            completion_rate=data.get('completion_rate'),
            likes=data.get('likes'),
            favorites=data.get('favorites'),
            shares=data.get('shares'),
            crawl_time=datetime.strptime(data.get('crawl_time'), '%Y-%m-%d %H:%M:%S')
        )
        session.add(record)
        session.commit()
        session.close()
        return record.id
    
    def get_hotspots_by_date(self, date):
        """按日期获取热点"""
        session = self.Session()
        records = session.query(HotspotRecord).filter(
            HotspotRecord.crawl_time >= date,
            HotspotRecord.crawl_time < date + timedelta(days=1)
        ).all()
        session.close()
        return records
    
    def get_all_publishes(self):
        """获取所有发布记录"""
        session = self.Session()
        records = session.query(PublishRecord).all()
        session.close()
        return records
    
    def update_memory(self, key, value):
        """更新记忆记录"""
        import json
        session = self.Session()
        record = session.query(MemoryRecord).filter_by(key=key).first()
        
        if record:
            record.value = json.dumps(value, ensure_ascii=False)
        else:
            record = MemoryRecord(
                key=key,
                value=json.dumps(value, ensure_ascii=False)
            )
            session.add(record)
        
        session.commit()
        session.close()
    
    def get_memory(self, key):
        """获取记忆记录"""
        import json
        session = self.Session()
        record = session.query(MemoryRecord).filter_by(key=key).first()
        session.close()
        
        if record:
            return json.loads(record.value)
        return None