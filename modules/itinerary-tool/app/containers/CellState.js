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
  const { date, fieldName, city } = ownProps
  return {
    getOptions: (input) => {
      return fetch('http://127.0.0.1:8000/search_text/', {
        method: 'post',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          csrfmiddlewaretoken: document.getElementsByName('csrfmiddlewaretoken')[0].getAttribute('value'),
          city: city,
          title: input,
          category: fieldName
        })
      }).then((response) => {
        return response.json()
      }).then((json) => {
        return { options: json['experiences'] }
      }).catch((exception) => {
        console.log('fetch failed', exception)
      })
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
