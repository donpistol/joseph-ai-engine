"""Unofficial ESPN public endpoints. Availability and schemas may change."""
import requests
import streamlit as st

BASE='https://site.api.espn.com/apis/site/v2/sports'
LEAGUES={'NBA':'basketball/nba','NFL':'football/nfl'}

@st.cache_data(ttl=600,show_spinner=False)
def fetch(path,params=None):
    r=requests.get(f'{BASE}/{path}',params=params,timeout=12,headers={'User-Agent':'Mozilla/5.0 (compatible; JosephAI/3.0)'})
    r.raise_for_status()
    return r.json()

def games(league,day):
    raw=fetch(f'{LEAGUES[league]}/scoreboard',{'dates':day.strftime('%Y%m%d'),'limit':100})
    return raw.get('events',[])

def team_schedule(league,team_id,season):
    raw=fetch(f'{LEAGUES[league]}/teams/{team_id}/schedule',{'season':season})
    return raw.get('events',[])

def roster(league,team_id):
    raw=fetch(f'{LEAGUES[league]}/teams/{team_id}/roster')
    athletes=raw.get('athletes',[])
    if athletes and 'items' in athletes[0]:
        return [p for group in athletes for p in group.get('items',[])]
    return athletes

def athlete_log(league,athlete_id,season):
    return fetch(f'{LEAGUES[league]}/athletes/{athlete_id}/gamelog',{'season':season})
