import { connect } from 'react-redux'
import { deleteItem } from '../actions'
import Cell from '../components/Cell'

const mapStateToProps = (state) => {

}

const mapDispatchToProps = (dispatch) => {

}

const ItemList = connect(
  mapStateToProps,
  mapDispatchToProps
)(Cell)

export default ItemList

