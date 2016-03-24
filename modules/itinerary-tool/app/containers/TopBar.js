import React from 'react'
import { connect } from 'react-redux'
import { changeTitle } from '../actions'

const TopBar = ({ dispatch }) => (
  <div className="top-bar">
    <div className="form-inline">
      <img src="https://tripalocal-static.s3.amazonaws.com/static/img/top_logo-en.svg" width="150" />
      <label forName="title">客人姓名</label>
      <input className="form-control" name="title" onChange={e => dispatch(changeTitle(e.target.value))}/>
      <label forName="start-date">开始日期</label>
      <input className="form-control" name="start-date" />
    </div> 
  </div>
)

export default connect()(TopBar)
