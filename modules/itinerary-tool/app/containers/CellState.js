import { connect } from 'react-redux'
import { showSelect, updateItems } from '../actions'
import Cell from '../components/Cell'

const mapStateToProps = (state, ownProps) => {
  const { date, fieldName } = ownProps
  return {
    showSelect: state.dates[date][fieldName]['display'] === 'EDIT' ? true : false
  }
}

const mapDispatchToProps = (dispatch, ownProps) => {
  const { date, fieldName } = ownProps
  return {
    getOptions: (input, callback) => {
      setTimeout(() => {
        callback(null, {
            options: [
                { id: 12345, title: 'Super Cool' },
                { id: 2935, title: 'Insanely Great' }
            ],
            complete: true
        });
      }, 500);
    },
    hideSelect: () => dispatch(showSelect(date, fieldName, 'NORMAL')),
    handleChange: (val) => dispatch(updateItems(date, fieldName, val))
  }
}

const CellState = connect(
  mapStateToProps,
  mapDispatchToProps
)(Cell)

export default CellState
