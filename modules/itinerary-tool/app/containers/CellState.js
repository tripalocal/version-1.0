import { connect } from 'react-redux'
import { showSelect, updateItems, updateThenSave } from '../actions'
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
    getOptions: (input, callback) => {
      fetch('/search_text/', {
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
        if (fieldName === 'experiences') {
          return json['experiences'].concat(json['suggestions'], json['products'])
        } else if (fieldName === 'transport') {
          return json['flights'].concat(json['transfers'])
        } else if (fieldName === 'accommodation') {
          return json['accommodations']
        } else {
          return []
        }
      }).then((results) => {
        callback(null, {
          options: results
        })
      }).catch((exception) => {
        console.log('fetch failed', exception)
      })
    },
    hideSelect: () => dispatch(showSelect(date, fieldName, 'NORMAL')),
    handleChange: (val) => dispatch(updateThenSave(updateItems, [date, fieldName, val]))
  }
}

const CellState = connect(
  mapStateToProps,
  mapDispatchToProps
)(Cell)

export default CellState
