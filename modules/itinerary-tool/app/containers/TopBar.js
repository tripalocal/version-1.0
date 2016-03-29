import React from 'react'
import { connect } from 'react-redux'
import { changeTitle, changeStartDate, changeGuests } from '../actions'

const TopBar = ({ title, startDate, dispatch }) => (
  <div className="top-bar">
    <div className="form-inline">
      <img src="https://tripalocal-static.s3.amazonaws.com/static/img/top_logo-en.svg" width="150" />
      <label forName="title">客人姓名</label>
      <input value={title} className="form-control" name="title" onChange={e => dispatch(changeTitle(e.target.value))}/>
      <label forName="start-date">开始日期</label>
      <div className="date-field">
        <input className="form-control" id="start-date" name="start-date" onBlur={e => dispatch(changeStartDate(e.target.value))} />
      </div>
      <div className="pull-right">
        <select className="form-control" onChange={e => dispatch(changeGuests(e.target.value))}>
          <option value="1">1人团</option>
          <option value="2">2人团</option>
          <option value="3">3人团</option>
          <option value="4">4人团</option>
          <option value="5">5人团</option>
          <option value="6">6人团</option>
          <option value="7">7人团</option>
          <option value="8">8人团</option>
          <option value="9">9人团</option>
          <option value="10">10人团</option>
        </select>
      </div>
    </div> 
  </div>
)

const mapStateToProps = (state) => {
  return {
    title: state.title
  }
}

export default connect(mapStateToProps)(TopBar)
