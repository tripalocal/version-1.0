import { connect } from 'react-redux'
import { initialize } from 'redux-form'
import { showModal, assignHost } from '../actions'
import Modal from '../components/Modal'

const mapStateToProps = (state) => {
  return {
    setting: state.modal['display'],
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    handleClose: () => dispatch(showModal('', '', 'NONE')),
  }
}

const ModalState = connect(
  mapStateToProps,
  mapDispatchToProps
)(Modal)

export default ModalState
