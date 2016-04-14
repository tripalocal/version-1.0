import React, { PropTypes } from 'react'
import Select from 'react-select'

const Cell = ({ date, city, field, fieldName, showSelect, hideSelect, getOptions, handleChange, handleClick }) => (
  <td style={{minWidth: '200px'}}>
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
        <button className="btn btn-default" style={{border: 0}} type="button" onClick={handleClick}>
            <span className="glyphicon glyphicon-pencil"></span>
          </button>
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
