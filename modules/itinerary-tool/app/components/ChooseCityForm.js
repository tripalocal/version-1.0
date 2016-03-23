import React from 'react'
import { reduxForm, initialize } from 'redux-form'
import { addDate, showModal } from '../actions'

const ChooseCityForm = ({ fields: { city, position }, handleSubmit, onSubmit, date }) => (
  <form onSubmit={handleSubmit}>
    <label forName="city">Choose a city</label>
    <select className="form-control" {...city} value={city.value || ''}>
      <option></option>
      <option>Melbourne</option>
      <option>Sydney</option>
      <option>Brisbane</option>
      <option>Gold Coast</option>
      <option>Adelaide</option>
    </select>
    <label forName="position">Before or After</label>
    <select className="form-control" {...position} value={position.value || ''}>
      <option></option>
      <option>Before</option>
      <option>After</option>
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
