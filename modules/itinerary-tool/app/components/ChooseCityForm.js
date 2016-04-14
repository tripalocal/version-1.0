import React from 'react'
import { reduxForm, initialize } from 'redux-form'
import { addDate, showModal } from '../actions'

const ChooseCityForm = ({ fields: { city, position }, handleSubmit, onSubmit, date }) => (
  <form onSubmit={handleSubmit}>
    <label forName="city">城市</label>
    <select className="form-control" {...city} value={city.value || ''}>
      <option></option>
      <option value="Melbourne" label="墨尔本">墨尔本</option>
      <option value="Sydney" label="悉尼">悉尼</option>
      <option value="Brisbane" label="布里斯班">布里斯班</option>
      <option value="Goldcoast" label="黄金海岸">黄金海岸</option>
      <option value="Adelaide" label="阿德莱德">阿德莱德</option>
      <option value="Hobart" label="霍巴特">霍巴特</option>
      <option value="Darwin" label="达尔文">达尔文</option>
      <option value="Wellington" label="惠灵顿">惠灵顿</option>
      <option value="Auckland" label="奥克兰">奥克兰</option>
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
