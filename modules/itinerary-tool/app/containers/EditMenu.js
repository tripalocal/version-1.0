import React from 'react'
import { connect } from 'react-redux'
import { showSelect, showModal } from '../actions'

let EditMenu = ({ dispatch, date, fieldName }) => (
  <ul className="dropdown-menu">
    <li>
      <a href="#" onClick={ e => {
        e.preventDefault()
        dispatch(showSelect(date, fieldName, 'EDIT'))
      }}>
        Edit
      </a>
    </li>
    <li>
      <a href="#" onClick={ e => {
        e.preventDefault()
        dispatch(showModal('ASSIGN_HOST'))
      }}>
        Assign host
      </a>
    </li>
  </ul>
)

EditMenu = connect()(EditMenu)

export default EditMenu
