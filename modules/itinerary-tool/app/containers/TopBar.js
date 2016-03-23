import React from 'react'
import { connect } from 'react-redux'
import { showModal, removeDate, moveDate, changeTitle } from '../actions'

const TopBar = ({ dispatch, showEditRowMenu, selectedDate }) => (
  <div className="bar-horizontal">
    {showEditRowMenu
      ? <div> 
          <button className="btn btn-secondary" onClick={e => dispatch(showModal(selectedDate, '', 'CHOOSE_CITY'))}>Add day</button>
          <button className="btn btn-secondary" onClick={e => dispatch(removeDate(selectedDate))}>Delete day</button>
          <button className="btn btn-secondary" onClick={e => dispatch(moveDate(selectedDate, 'BACK'))}>Move day back</button>
          <button className="btn btn-secondary" onClick={e => dispatch(moveDate(selectedDate, 'FORWARD'))}>Move day forward</button>
        </div>
      : <div className="form-inline"> 
          <label forName="title">Title</label>
          <input style={{marginRight:'20px'}} className="form-control" name="title" onChange={e => dispatch(changeTitle(e.target.value))}/>
          <label forName="start-date">Start Date</label>
          <input className="form-control" name="start-date" />
        </div>} 
  </div>
)

const mapStateToProps = (state) => {
  return {
    showEditRowMenu: state.selected == '' ? false : true,
    selectedDate: state.selected,
  }
}

export default connect(mapStateToProps)(TopBar)
