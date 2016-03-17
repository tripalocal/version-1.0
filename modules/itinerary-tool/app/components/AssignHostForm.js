import React, { PropTypes } from 'react'
import { reduxForm, initialize } from 'redux-form'
import { assignHost, showModal } from '../actions'

const AssignHostForm = ({ fields: { host }, handleSubmit, dispatch, date, field }) => (
  <form onSubmit={handleSubmit}>
    <div className="form-group">
      <label forName="host">Assign Host</label>
      <select className="form-control" name="host" {...host}>
        <option>Bob</option>
        <option>Sally</option>
      </select>
    </div>
    <button className="btn btn-primary" type="submit">Submit</button>
  </form>
)

const mapStateToProps = (state) => {
  return {
    date: state.modal['date'],
    field: state.modal['display']
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    handleSubmit: (event, data) => {
      event.preventDefault()
      dispatch(assignHost(date, field, data['host']))
      dispatch(showModal('NONE'))
      dispatch(initialize('assignHost', {}))
    }
  }
}

export default reduxForm({
  form: 'assignHost',
  fields: ['host']
}, mapStateToProps, mapDispatchToProps)(AssignHostForm)
