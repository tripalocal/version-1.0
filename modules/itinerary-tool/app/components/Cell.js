import React, { PropTypes } from 'react'
import Select from 'react-select'

const Cell = ({ date, city, field, fieldName, bookings, showSelect, hideSelect, getOptions, handleChange, handleClick }) => (
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
        {field['items'].map(item => <span className="badge" style={badgeStyles[bookings.filter(booking => {return booking.id == item.id})[0].host]} key={item.id}>{item.title}</span>)}
        <button className="btn btn-default" style={{border: 0}} type="button" onClick={handleClick}>
            <span className="glyphicon glyphicon-pencil"></span>
          </button>
      </div>
    }
  </td>
)

const badgeStyles = {
  'None': { 'marginRight': '5px' },
  'tripalocal': { 'marginRight': '5px', 'borderColor': '#99CCCC', 'backgroundColor': '#E6F4F3' },
  'host1': { 'marginRight': '5px', 'borderColor': '#99CC99', 'backgroundColor': '#D8EAD8' },
  'host2': { 'marginRight': '5px', 'borderColor': '#CCCC99', 'backgroundColor': '#EAE9D6' },
  'host3': { 'marginRight': '5px', 'borderColor': '#CC9999', 'backgroundColor': '#EAD8D8' },
  'host4': { 'marginRight': '5px', 'borderColor': '#CC99CC', 'backgroundColor': '#EEDCEF' }
}

Cell.propTypes = {
  date: PropTypes.string,
  field: PropTypes.object,
  getOptions: PropTypes.func,
  showSelect: PropTypes.bool,
  hideSelect: PropTypes.func,
  handleChange: PropTypes.func
}

export default Cell
