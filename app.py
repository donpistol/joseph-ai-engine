import math
from datetime import date,timedelta
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import norm
from data_sources import games,team_schedule,roster,athlete_log

st.set_page_config(page_title='Joseph AI V3',page_icon='🧠',layout='wide')
st.title('🧠 Joseph AI V3 · Automatic Matchup Intelligence')
st.caption('Free-data prototype • No paid APIs • No manual averages or standard deviations')
st.warning('Experimental model, NOT validated betting predictions. Public ESPN endpoints are unofficial and may fail or omit data. No automatic Hard Rock odds feed.')
league=st.selectbox('League',['NBA','NFL'])
day=st.date_input('Game date',date.today())

def participants(event):
    comp=(event.get('competitions') or [{}])[0]
    teams=comp.get('competitors',[])
    home=next((x for x in teams if x.get('homeAway')=='home'),None)
    away=next((x for x in teams if x.get('homeAway')=='away'),None)
    return away,home

def name(team):return team.get('team',{}).get('displayName','Unknown') if team else 'Unknown'

def recent_scores(league,team_id,season,before,n=12):
    events=team_schedule(league,team_id,season)
    rows=[]
    for event in events:
        if str(event.get('date',''))[:10]>=before.isoformat():continue
        away,home=participants(event)
        if not away or not home:continue
        status=event.get('status',{}).get('type',{}).get('completed',False)
        if not status:continue
        mine=next((t for t in (away,home) if str(t.get('team',{}).get('id'))==str(team_id)),None)
        other=next((t for t in (away,home) if t is not mine),None)
        if not mine or not other:continue
        try:
            scored=float(mine['score']['value'] if isinstance(mine['score'],dict) else mine['score'])
            allowed=float(other['score']['value'] if isinstance(other['score'],dict) else other['score'])
        except (KeyError,ValueError,TypeError):continue
        rows.append({'date':str(event.get('date',''))[:10],'scored':scored,'allowed':allowed,'win':int(scored>allowed)})
    return pd.DataFrame(rows).sort_values('date').tail(n) if rows else pd.DataFrame()

def log_rows(raw,league):
    # ESPN gamelog structure: labels in names and stats indexed by categories.
    labels=[]
    for cat in raw.get('labels',[]):
        if isinstance(cat,str):labels.append(cat)
    if not labels:
        for cat in raw.get('categories',[]):
            labels.extend(cat.get('labels',[]))
    events=raw.get('events',{})
    rows=[]
    for season in raw.get('seasonTypes',[]):
        for cat in season.get('categories',[]):
            local=cat.get('labels',[]) or labels
            for entry in cat.get('events',[]):
                eid=str(entry.get('eventId') or entry.get('id') or '')
                vals=entry.get('stats',[])
                if not vals or not isinstance(vals,list):continue
                d=dict(zip(local,vals))
                d['date']=str(events.get(eid,{}).get('gameDate',''))[:10]
                rows.append(d)
    return pd.DataFrame(rows)

def numeric_col(df,keys):
    for key in keys:
        for c in df.columns:
            if str(c).upper()==key.upper():
                return pd.to_numeric(df[c],errors='coerce').dropna()
    return pd.Series(dtype=float)

try:
    with st.spinner('Retrieving live schedule…'):
        events=games(league,day)
except Exception as exc:
    st.error('Free schedule feed unavailable. Try again later or choose another date. No results were invented.')
    st.caption(f'Data source error: {str(exc)[:180]}')
    st.stop()
if not events:
    st.info('No games returned for this date. Select another date.')
    st.stop()
choices={f"{name(participants(e)[0])} @ {name(participants(e)[1])} — {e.get('shortName','')}":e for e in events}
event=choices[st.selectbox('Choose matchup',list(choices))]
away,home=participants(event)
if not away or not home:
    st.error('Team information unavailable for this event.')
    st.stop()
st.subheader(f'{name(away)} @ {name(home)}')
st.caption('Status: '+event.get('status',{}).get('type',{}).get('description','Unknown'))
season=day.year if league=='NFL' or day.month>=9 else day.year-1
team_ids=[away['team']['id'],home['team']['id']]
try:
    with st.spinner('Retrieving previous game results…'):
        histories=[recent_scores(league,t,season,day) for t in team_ids]
except Exception as exc:
    st.error('Team history feed unavailable; matchup projections withheld.')
    st.caption(str(exc)[:180]);histories=[pd.DataFrame(),pd.DataFrame()]
if all(len(h)>=5 for h in histories):
    # Simple opponent-agnostic baseline; no claim of trained accuracy.
    a,h=histories
    a_score=(a.scored.mean()+h.allowed.mean())/2
    h_score=(h.scored.mean()+a.allowed.mean())/2
    margin=h_score-a_score
    # Heuristic volatility, deliberately not represented as calibrated.
    spread_sd=max(8.0 if league=='NBA' else 10.0,float(np.std(np.r_[a.scored-a.allowed,h.scored-h.allowed],ddof=1)))
    home_prob=norm.cdf(margin/spread_sd)
    c1,c2,c3=st.columns(3)
    c1.metric('Away projected points',f'{a_score:.1f}')
    c2.metric('Home projected points',f'{h_score:.1f}')
    c3.metric('Home win probability (experimental)',f'{home_prob:.0%}')
    st.caption(f'Using {len(a)} away-team games and {len(h)} home-team games. Simple scoring/allowing averages, no injuries or opponent-strength adjustment. Win probabilities are NOT calibrated.')
    st.dataframe(pd.DataFrame([{'Team':name(away),'Games':len(a),'Points for':round(a.scored.mean(),1),'Points allowed':round(a.allowed.mean(),1),'Recent wins':int(a.win.sum())},{'Team':name(home),'Games':len(h),'Points for':round(h.scored.mean(),1),'Points allowed':round(h.allowed.mean(),1),'Recent wins':int(h.win.sum())}]),hide_index=True,use_container_width=True)
else:
    st.info('Insufficient completed team games for a meaningful baseline (need at least five per team). No matchup probability shown.')

st.divider()
st.subheader('🎯 Player specialty explorer')
st.caption('Select a player. The engine attempts to retrieve their season game logs and calculate recent category trends automatically.')
side=st.radio('Team',[name(away),name(home)],horizontal=True)
selected=away if side==name(away) else home
try:
    people=roster(league,selected['team']['id'])
    people=[p for p in people if p.get('id') and p.get('displayName')]
except Exception as exc:
    st.error('Roster unavailable from free feed.');st.caption(str(exc)[:180]);st.stop()
if not people:
    st.info('No player roster returned.');st.stop()
players={p['displayName']:p for p in people}
p=players[st.selectbox('Player',sorted(players))]
try:
    raw=athlete_log(league,p['id'],season)
    logs=log_rows(raw,league)
except Exception as exc:
    st.error('Game-log feed unavailable for this player.');st.caption(str(exc)[:180]);st.stop()
if logs.empty:
    st.info('The public game-log feed did not provide readable player game statistics. No projection generated.')
else:
    st.caption('Source: ESPN public game-log endpoint. Check the columns below; schema may change.')
    st.dataframe(logs.tail(15),hide_index=True,use_container_width=True)
    categories={'NBA':{'Points':['PTS'],'Rebounds':['REB'],'Assists':['AST'],'Three-pointers':['3PM','3PTM']},'NFL':{'Passing yards':['YDS','PASS YDS'],'Receptions':['REC'],'Receiving yards':['REC YDS'],'Rushing yards':['RUSH YDS']}}[league]
    stat=st.selectbox('Specialty',list(categories))
    values=numeric_col(logs,categories[stat]).tail(15)
    if len(values)>=5:
        mean=float(values.mean());sd=float(values.std(ddof=1))
        st.metric('Recent average',f'{mean:.1f}')
        st.metric('Recent standard deviation',f'{sd:.1f}')
        st.line_chart(values.reset_index(drop=True))
        st.caption(f'{len(values)} readable games. Descriptive history only, not a verified future hit probability.')
    else:
        st.info('Not enough matching numeric game-log data for this specialty. No estimate shown.')

st.divider()
st.subheader('📷 Hard Rock screenshot support')
shot=st.file_uploader('Attach Hard Rock screenshot (PNG/JPG)',type=['png','jpg','jpeg'])
if shot:
    st.image(shot,caption='Screenshot received')
    st.info('This free V3 build does not automatically read screenshot text. Image OCR is a future optional upgrade; it will not fabricate odds.')
st.caption('Free hosting may sleep when idle. ESPN endpoints are unofficial. This prototype does not place bets, connect to Hard Rock, or promise an 85–90% hit rate.')
