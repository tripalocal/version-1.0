import React from 'react'
import { connect } from 'react-redux'

const SideBar = ({ }) => (
  <div className="side-bar">
    <table className="table">
      <thead>
        <tr className="table-header">
          <th>项目</th>
          <th>单位</th>
          <th>报价</th>
          <th>数量</th>
          <th>小计</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>奥克兰5星</td>
          <td>每晚</td>
          <td>300</td>
          <td>2</td>
          <td>600</td>
        </tr>
        <tr>
          <td>墨尔本街头美食之旅</td>
          <td>每晚</td>
          <td>200</td>
          <td>1</td>
          <td>200</td>
        </tr>
        <tr>
          <td>大隐于市的当代艺术馆</td>
          <td>每晚</td>
          <td>156</td>
          <td>5</td>
          <td>738</td>
        </tr>
        <tr>
          <td>大隐于市的当代艺术馆</td>
          <td>每晚</td>
          <td>123</td>
          <td>5</td>
          <td>857</td>
        </tr>
      </tbody>
    </table>
    <div className="bottom-bar">
      <table className="table">
        <thead>
          <tr>
            <th>澳元成本</th> 
            <th>利润</th> 
            <th>人民币</th> 
            <th>人民币每人</th> 
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>7956</td>
            <td>8840</td>
            <td>44200</td>
            <td>22100</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
)

const mapStateToProps = (state) => {
  return {

  }
}

const mapDispatchToProps = (dispatch) => {
  return {

  }
}

export default connect(mapStateToProps, mapDispatchToProps)(SideBar)
