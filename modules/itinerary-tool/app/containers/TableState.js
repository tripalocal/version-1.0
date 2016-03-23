import { connect } from 'react-redux'
import Table from '../components/Table'

const mapStateToProps = (state) => {
  return {
    dates: state.dates
  }
}

const TableState = connect(mapStateToProps)(Table)

export default TableState

