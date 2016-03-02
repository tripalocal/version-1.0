import React from 'react'
import { connect } from 'react-redux'
import Bar from '../components/Bar'
import TableContainer from './TableContainer'
import ModalContainer from './ModalContainer'

export const App = ({ showModal }) => (
  <div>
    <Bar />
    <TableContainer />
    { showModal !== 'NONE'
      ? <ModalContainer />
      : null }
  </div>
)

const mapStateToProps = (state) => {
    return { showModal: state.modal }
}

export default connect(mapStateToProps)(App)

