import React from 'react'
import { connect } from 'react-redux'
import Bar from '../components/Bar'
import TableState from './TableState'
import ModalState from './ModalState'

export const App = ({ showModal }) => (
  <div>
    <Bar />
    <TableState />
    { showModal !== 'NONE'
      ? <ModalState />
      : null }
  </div>
)

const mapStateToProps = (state) => {
  return { showModal: state.modal['display'] }
}

export default connect(mapStateToProps)(App)

