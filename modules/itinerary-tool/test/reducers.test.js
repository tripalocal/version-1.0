import { expect } from 'chai'
import reducer from '../app/reducers.js'

describe('Reducers', () => {
  describe('modal', () => {
    it('should return the initial state', () => {
      expect(
        reducer(undefined, {})
      ).to.eql(
        {
          modal: {date: '', field: '', display: 'NONE'},
          dates: {},
          form: {},
          selected: ""
        }
      )
    })

    it('should handle SHOW_MODAL', () => {
      expect(
        reducer({}, {
          type: 'SHOW_MODAL',
          date: '2016-03-04',
          field: 'experiences',
          setting: 'NEW_ITEM'
        })
      ).to.eql(
        {
          modal: {date: '2016-03-04', field: 'experiences', display: 'NEW_ITEM'},
          dates: {},
          form: {},
          selected: ""
        }
      )
    })
  })

  describe('dates', () => {
    it('should return the initial state', () => {
      expect(
        reducer(undefined, {})
      ).to.eql(
        {
          modal: {date: '', field: '', display: 'NONE'},
          dates: {},
          form: {},
          selected: ""
        }
      )
    })

    it('should handle SHOW_SELECT', () => {
    })

    it('should handle ADD_DATE', () => {
      expect(
        reducer({}, {
          type: 'ADD_DATE',
          date: '2016-03-10'
        })
      ).to.eql(
        {
          modal: {date: '', field: '', display: 'NONE'},
          dates: {
            '2016-03-10': {'city': '', 'experiences': { 'items': [], 'host': '', 'display': 'NORMAL' }, 'transport': {'items': [], 'host': '', 'display': 'NORMAL'}, 'accommodation': {'items': [], 'host': '', 'display': 'NORMAL'}, 'restaurants': {'items': [], 'host': '', 'display': 'NORMAL'}}
          },
          form: {},
          selected: ""
        }
      )
    })

    it('should handle REMOVE_DATE', () => {
      expect(
        reducer(
          {
            modal: {date: '', field: '', display: 'NONE'},
            dates: {
              '2016-03-10': {'city': 'melbourne', 'experiences': { 'items': [], 'host': '', 'display': 'NORMAL' }, 'transport': {'items': [], 'host': '', 'display': 'NORMAL'}, 'accommodation': {'items': [], 'host': '', 'display': 'NORMAL'}, 'restaurants': {'items': [], 'host': '', 'display': 'NORMAL'}}
            },
            form: {},
            selected: ""
          },
          {
            type: 'REMOVE_DATE',
            date: '2016-03-10'
          }
        )
      ).to.eql(
        {
          modal: {date: '', field: '', display: 'NONE'},
          dates: {},
          form: {},
          selected: ""
        }
      )
    })

    it('should handle MOVE_DATE', () => {
      expect(
        reducer(
          {
            modal: {date: '', field: '', display: 'NONE'},
            dates: {
              '2016-03-10': {'city': 'melbourne', 'experiences': { 'items': [], 'host': '', 'display': 'NORMAL' }, 'transport': {'items': [], 'host': '', 'display': 'NORMAL'}, 'accommodation': {'items': [], 'host': '', 'display': 'NORMAL'}, 'restaurants': {'items': [], 'host': '', 'display': 'NORMAL'}},
              '2016-03-11': {'city': 'sydney', 'experiences': { 'items': [], 'host': '', 'display': 'NORMAL' }, 'transport': {'items': [], 'host': '', 'display': 'NORMAL'}, 'accommodation': {'items': [], 'host': '', 'display': 'NORMAL'}, 'restaurants': {'items': [], 'host': '', 'display': 'NORMAL'}}
            },
            form: {},
            selected: ""
          },
          {
            type: 'MOVE_DATE',
            oldDate: '2016-03-10',
            newDate: '2016-03-11'
          }
        )
      ).to.eql(
        {
          modal: {date: '', field: '', display: 'NONE'},
          dates: {
            '2016-03-11': {'city': 'melbourne', 'experiences': { 'items': [], 'host': '', 'display': 'NORMAL' }, 'transport': {'items': [], 'host': '', 'display': 'NORMAL'}, 'accommodation': {'items': [], 'host': '', 'display': 'NORMAL'}, 'restaurants': {'items': [], 'host': '', 'display': 'NORMAL'}},
            '2016-03-10': {'city': 'sydney', 'experiences': { 'items': [], 'host': '', 'display': 'NORMAL' }, 'transport': {'items': [], 'host': '', 'display': 'NORMAL'}, 'accommodation': {'items': [], 'host': '', 'display': 'NORMAL'}, 'restaurants': {'items': [], 'host': '', 'display': 'NORMAL'}}
          },
          form: {},
          selected: ""
        }
      )
    })
  })
})
