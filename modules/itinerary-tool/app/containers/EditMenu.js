import React from 'react'
import { connect } from 'react-redux'
import { showSelect, showModal } from '../actions'

const EditMenu = ({ dispatch, date, fieldName }) => (
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
        dispatch(showModal(date, fieldName, 'ASSIGN_HOST'))
      }}>
        Assign host
      </a>
    </li>
  </ul>
)

export default connect()(EditMenu)

