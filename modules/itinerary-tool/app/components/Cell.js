import React, { PropTypes } from 'react'
import Select from 'react-select'
import EditMenu from '../containers/EditMenu'

const Cell = ({ date, city, field, fieldName, showSelect, hideSelect, getOptions, handleChange }) => (
  <td>
    { showSelect 
    ? 
      <Select.Async
        loadOptions={getOptions}
        onBlur={hideSelect}
        value={field['items']}
        labelKey="title"
        valueKey="id"
        onChange={handleChange}
        clearable={false}
        minimumInput={1}
        multi
      />
    : 
      <div>
        {field['items'].map(item => <span className="badge"style={{marginRight: '5px'}} key={item.id}>{item.title}</span>)}
        <div className="dropdown" style={{display: 'inline-block'}}>
          <button className="btn btn-default" style={{border: 0}} type="button" data-toggle="dropdown">
            <span className="glyphicon glyphicon-pencil"></span>
          </button>
          <EditMenu key={date + fieldName + 'menu'} date={date} fieldName={fieldName} />
        </div>
      </div>
    }
  </td>
)

Cell.propTypes = {
  date: PropTypes.string,
  field: PropTypes.object,
  getOptions: PropTypes.func,
  showSelect: PropTypes.bool,
  hideSelect: PropTypes.func,
  handleChange: PropTypes.func
}

export default Cell
