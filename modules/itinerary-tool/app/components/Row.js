import React, { PropTypes } from 'react'
import ItemList from '../containers/ItemList'

const Row = ({ date }) => (
  <tr> 
    {
      Object.keys(date).map(field => {
        if (field === 'city' || field === 'date') {
          return <td>{fields}</td>
        }
        return(
          <ItemList field={field} />
        )
      })
    }
  </tr>
)

Row.propTypes = {
  fields: PropTypes.arrayOf(PropTypes.shape({
    city: PropTypes.string,
    experiences: PropTypes.object,
    transport: PropTypes.object,
    accommodation: PropTypes.object,
    restaurants: PropTypes.object
  })),
}

export default Row
