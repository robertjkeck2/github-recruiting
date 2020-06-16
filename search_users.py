import json

from flask import Flask, render_template, flash, request
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField

from config import GITHUB_USERNAME, GITHUB_PASSWORD


SEARCH_URL = 'https://api.github.com/search/users?q='
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'


class ReusableForm(Form):
    name = TextField('Name:', validators=[validators.required()])

@app.route('/', methods=['GET', 'POST'])
def home():
    form = ReusableForm(request.form)
    if request.method == 'POST':
        username = request.form['name']
        language = 'Python'
        user_stats = stats(username)
        user_repos = repos(username, language)
        data = {'username': username, 'repos': user_repos, 'stats': user_stats}
        return render_template('user.html', data=data)
    return render_template('home.html', form=form)

def search(user):
    _, users = search_users(search_name=user)
    return users[0]

def stats(user):
    _, users = search_users(search_name=user)
    language_stats = get_user_stats(users[0])
    return language_stats

def repos(user, language):
    _, users = search_users(search_name=user)
    repos = get_user_repos(users[0], language)
    return repos

def execute_request(url):
    response = requests.get(
        url,
        auth=HTTPBasicAuth(GITHUB_USERNAME, GITHUB_PASSWORD))
    return response.json()

def export_to_excel(user_data, filename):
    df = pd.DataFrame(user_data)
    df.to_csv(filename)

def search_users(filename=None, language=None, repo_count=None, location=None, search_name=None):
    search_query = 'type:user'
    if language:
        search_query = search_query + ' language:' + language
    if repo_count:
        search_query = search_query + ' repos:>' + str(repo_count)
    if location:
        search_query = search_query + ' location:' + location
    if search_name:
        search_query = search_query + ' ' + search_name + ' in:login'
    url = SEARCH_URL + search_query
    user_data = execute_request(url)
    if filename:
        export_to_excel(user_data['items'], filename)
    total_count = user_data.get('total_count')
    return total_count, user_data['items']

def get_user_stats(user):
    language_stats = {}
    repos_url = user.get('repos_url', None)
    if repos_url:
        repo_data = execute_request(repos_url)
    for repo in repo_data:
        language_count = language_stats.get(repo['language'], 0)
        language_stats[repo['language']] = language_count + 1
    sorted_stats = sorted(language_stats.items(), key=lambda kv: kv[1])
    sorted_stats.reverse()
    return sorted_stats

def get_user_repos(user, language):
    repos = []
    repos_url = user.get('repos_url', None)
    if repos_url:
        repo_data = execute_request(repos_url)
    for repo in repo_data:
        if repo['language'] == language:
            repos.append(repo['html_url'])
    return repos

if __name__ == '__main__':
    app.run(debug=True)
