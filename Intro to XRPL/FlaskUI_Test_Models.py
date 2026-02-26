from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
from SecondXRPL import *


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    wallet_address = db.Column(db.String(100), nullable=False)
    nfts = db.relationship('NFT', backref='owner', lazy=True)

class NFT(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    nft_id = db.Column(db.String(200), nullable=False)


from SecondXRPL import *



