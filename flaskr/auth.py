#!/usr/bin/env python3

import functools

from flask import (
	Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# @bp.route associates the URL /register with the register view function
@bp.route('/register', methods=('GET', 'POST'))
def register():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		db = get_db()
		error = None
		
		if not username:
			error = 'Username is required.'
		elif not password:
			error = 'Password is required.'
		elif db.execute(
			'SELECT id FROM user WHERE username = ?', (username,)
		).fetchone() is not None:
			error = 'User {} is already registered.'.format(username)
		
		if error is None:
			db.execute(
				'INSERT INTO user (username, password) VALUES (?, ?)',
				(username, generate_password_hash(password))
			)
			db.commit()
			return redirect(url_for('auth.login'))
		
		flash(error)
		
	return render_template('auth/register.html')

# @bp.route associates the URL /login with the register view function
@bp.route('/login', methods=('GET', 'POST'))
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		db = get_db()
		error = None
		
		"""
		fetchone() returns one row from the query.
		fetchall() is used, which returns a list of all results
		"""
		user = db.execute(
			'SELECT * FROM user WHERE username = ?', (username,)
		).fetchone()
		
		if user is None:
			error = 'Incorrect username.'
		elif not check_password_hash(user['password'], password):
			error = 'Incorrect password.'
			
		if error is None:
			session.clear()
			session['user_id'] = user['id']
			return redirect(url_for('index'))
		
		flash(error)
		
	return render_template('auth/login.html')

"""
bp.before_app_request() registers a function that runs before the view function,
no matter what URL is requested.
"""
@bp.before_app_request
def load_logged_in_user():
	user_id = session.get('user_id')
	
	if user_id is None:
		g.user = None
	else:
		g.user = get_db().execute(
			'SELECT * FROM user WHERE id = ?', (user_id,)
		).fetchone()

@bp.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('index'))

# Require Authentication in Other Views
def login_required(view):
	"""
	Decorator that checks if a user is loaded and redirects to the login page 
	otherwise. If a user is loaded the original view is called and continues 
	normally
	"""
	@functools.wraps(view)
	def wrapped_view(**kwargs):
		if g.user is None:
			# url_for: generates the URL to a view based on a name and arguments
			return redirect(url_for('auth.login'))
		
		return view(**kwargs)
	
	return wrapped_view