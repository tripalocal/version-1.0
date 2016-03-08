import React, { PropTypes } from 'react'
import { reduxForm } from 'redux-form'

let AssignHostForm = ({ fields: { host }, handleSubmit }) => (
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

AssignHostForm = reduxForm({
  form: 'assignHost',
  fields: ['host']
})(AssignHostForm)

export default AssignHostForm
