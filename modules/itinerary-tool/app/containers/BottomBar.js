import React from 'react'
import { connect } from 'react-redux'
import { showModal, removeDate, moveDate, updateThenSave } from '../actions'

const BottomBar = ({ dispatch, showEditRowMenu, selectedDate }) => (
  <div style={showEditRowMenu} className="bottom-bar edit-row">
    <div className="menu">
      <button className="btn btn-secondary" onClick={e => dispatch(showModal(selectedDate, '', 'CHOOSE_CITY'))}>
        <img src="https://tripalocal-static.s3.amazonaws.com/static/experiences/img/day_after.svg" width="30" height="30"/>
        加一天 
      </button>
      <button className="btn btn-secondary" onClick={e => dispatch(updateThenSave(removeDate, [selectedDate]))}>
        <img src="https://tripalocal-static.s3.amazonaws.com/static/experiences/img/delete.svg" width="30" height="30"/>
        删除当天 
      </button>
      <button className="btn btn-secondary" onClick={e => dispatch(updateThenSave(moveDate, [selectedDate, 'BACK']))}>
        <img src="https://tripalocal-static.s3.amazonaws.com/static/experiences/img/move_before.svg" width="30" height="30"/>
        往上移一天 
      </button>
      <button className="btn btn-secondary" onClick={e => dispatch(updateThenSave(moveDate, [selectedDate, 'FORWARD']))}>
        <img src="https://tripalocal-static.s3.amazonaws.com/static/experiences/img/move_after.svg" width="30" height="30"/>
        往下移一天 
      </button>
    </div>
  </div>
)

const mapStateToProps = (state) => {
  return {
    showEditRowMenu: state.selected == '' ? {display: 'none'} : {},
    selectedDate: state.selected
  }
}

export default connect(mapStateToProps)(BottomBar)
