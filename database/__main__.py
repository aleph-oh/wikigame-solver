#!/usr/bin/env python3
from .constants import engine, Base

Base.metadata.create_all(bind=engine)
