import React from 'react'
import { reduxForm, initialize } from 'redux-form'
import { addDate, showModal } from '../actions'

const ChooseCityForm = ({ fields: { city, position }, handleSubmit, onSubmit, date }) => (
  <form onSubmit={handleSubmit}>
    <label forName="city">城市</label>
    <select className="form-control" {...city} value={city.value || ''}>
      <option></option>
      <option>Melbourne</option>
      <option>Sydney</option>
      <option>Brisbane</option>
      <option>Goldcoast</option>
      <option>Adelaide</option>
      <option>Hobart</option>
      <option>Darwin</option>
      <option>Wellington</option>
      <option>Auckland</option>
    </select>
    <label forName="position">前/后</label>
    <select className="form-control" {...position} value={position.value || ''}>
      <option></option>
      <option value="BEFORE">前面加一天</option>
      <option value="AFTER">后面加一天</option>
    </select>
    <button className="btn btn-primary" type="submit">Submit</button>
  </form>
)

const mapStateToProps = (state) => {
  return {
  }
}

const mapDispatchToProps = (dispatch, ownProps) => {
  return {
    onSubmit: (data) => {
      dispatch(addDate(ownProps.date, data['city'], data['position']))
      dispatch(showModal('', '', 'NONE'))
      dispatch(initialize('chooseCity', {}, ['city', 'position']))
    }
  }
}

export default reduxForm({
  form: 'chooseCity',
  fields: ['city', 'position']
}, mapStateToProps, mapDispatchToProps)(ChooseCityForm)
