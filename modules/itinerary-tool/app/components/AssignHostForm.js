import React, { PropTypes } from 'react'
import { reduxForm } from 'redux-form'

let AssignHostForm = ({ fields: { host }, handleSubmit }) => {
  <form onSubmit={handleSubmit}>
    <label forName="host">Assign Host</label>
    <select name="host" {...host}>
      <option>Bob</option>
      <option>Sally</option>
    </select>
    <button type="submit">Submit</button>
  </form>
}

AssignHostForm = reduxForm({
  form: 'assignHost',
  fields: ['host']
})

export default AssignHostForm
