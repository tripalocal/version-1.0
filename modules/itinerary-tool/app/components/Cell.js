import React, { PropTypes } from 'react'
import Select from 'react-select'
import EditMenu from '../containers/EditMenu'

const Cell = ({ type, items, searchItems, handleChange, showSelect }) => (
  <td>
    {items.map(item => <span data-id="item.id">{item.title}</span>)}
    {showSelect ? 
      <Select.Async
        loadOptions={searchItems}
        placeholder={type}
        onChange={handleChange}
        clearable={false}
        multi
      />
      : null
    }
    <div className="dropdown">
      <button type="button" data-toggle="dropdown">
        <span className="caret"></span>
      </button>
      <EditMenu />
    </div>
  </td>
)

Cell.propTypes = {
  type: PropTypes.string,
  items: PropTypes.arrayOf(PropTypes.shape({
    title: PropTypes.string,
    id: PropTypes.number
  })),
  searchItems: PropTypes.func,
  handleChange: PropTypes.func
}

export default Cell
