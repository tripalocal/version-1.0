import { connect } from 'react-redux'
import { initialize } from 'redux-form'
import fetch from 'fetch'
import Modal from '../components/Modal'

const submitForm = (dispatch) => {
  fetch('http://www.tripalocal.com/itinerary', {
    method: 'POST',
    body: JSON.stringify(data)
  }).then((response) => {
    response.ok ? console.log("fetch success") : console.log("fetch fail")
    dispatch(showModal('NONE'))
    dispatch(initialize('newItem', {}))
    dispatch(initialize('assignHost', {}))
  }, (error) => {
    console.log('fetch error')
    dispatch(showModal('NONE'))
    dispatch(initialize('newItem', {}))
    dispatch(initialize('assignHost', {}))
  })
}

const mapStateToProps = (state) => {
  return {
    type: state.modal,
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    handleClose: dispatch(showModal('NONE')),
    handleSubmit: submitForm(dispatch)
  }
}

const ModalState = connect(
  mapStateToProps,
  mapDispatchToProps
)(Modal)

export default ModalState
