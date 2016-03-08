import { connect } from 'react-redux'
import { initialize } from 'redux-form'
import { showModal } from '../actions'
//import fetch from 'fetch'
import Modal from '../components/Modal'

const submitForm = (dispatch, data) => {
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
    setting: state.modal,
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    handleClose: () => dispatch(showModal('NONE')),
    handleSubmit: (data) => submitForm(dispatch,data)
  }
}

const ModalState = connect(
  mapStateToProps,
  mapDispatchToProps
)(Modal)

export default ModalState
