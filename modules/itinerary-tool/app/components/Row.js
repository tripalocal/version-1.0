import React, { PropTypes } from 'react'
import ItemList from '../containers/ItemList'

const Row = ({ fields }) => (
  <tr> 
  {Object.keys(fields).map(field =>
    if (field === 'date') {
      return <td>{fields.field}</td>
    }
    return(
      <ItemList />
    )
  )}
  </tr>
)

Row.propTypes = {
  fields: PropTypes.arrayOf(PropTypes.shape({

  })),
}

export default Row
