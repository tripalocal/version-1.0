import React, { PropTypes } from 'react'
import Row from './Row'
import BottomBar from '../containers/BottomBar'

const Table = ({ dates }) => (
  <div className="center">
    <table className="table">
      <thead>
        <tr className="table-header">
          <th>日期</th>
          <th>城市</th>
          <th>游玩地点和项目</th>
          <th>交通</th>
          <th>住宿</th>
        </tr>
      </thead>
      <tbody>
        {Object.keys(dates).sort((a,b) => new Date(a) - new Date(b)).map(date => <Row key={date} date={date} fields={dates[date]} />)}
      </tbody>
    </table>
    <BottomBar />
  </div>
)

Table.propTypes = {
  dates: PropTypes.object
}

export default Table
