import React, { PropTypes } from 'react'
import CellState from '../containers/CellState'
import { connect } from 'react-redux'
import { selectDate } from '../actions'

export const Row = ({ date, isSelected, fields, dispatch }) => (
  <tr className={isSelected} onClick={e => dispatch(selectDate(date))}>
    <td>{date}</td>
    <td>{fields['city']}</td>
    <CellState date={date} city={fields['city']} key={date + 'experiences'} fieldName="experiences" field={fields['experiences']} />
    <CellState date={date} city={fields['city']} key={date + 'transport'} fieldName="transport" field={fields['transport']} />
    <CellState date={date} city={fields['city']} key={date + 'accommodation'} fieldName="accommodation" field={fields['accommodation']} />
  </tr>
)

const mapStateToProps = (state, ownProps) => {
  return {
    isSelected: state.selected == ownProps.date ? "selected" : "" 
  }
}

export default connect(mapStateToProps)(Row)
