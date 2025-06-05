import { useFootnotesStore } from '@/stores/studies-footnotes'
import dataFormating from '@/utils/dataFormating'

const footnotesStore = useFootnotesStore()

function getSoaRowClasses(row) {
  if (row.cells && row.cells.length) {
    if (row.cells[0].style === 'soaGroup') {
      return 'flowchart'
    }
    if (row.cells[0].style === 'group') {
      return 'group'
    }
    if (row.cells[0].style === 'subGroup') {
      return 'subgroup'
    }
  }
  return 'bg-white'
}

function getSoaRowType(row) {
  return row.cells[0].style
}

function getSoaFirstCellClasses(cell) {
  let result = 'sticky-column'
  if (cell.style === 'soaGroup' || cell.style === 'group') {
    result += ' text-strong'
  } else if (cell.style === 'subGroup') {
    result += ' subgroup'
  }
  return result
}

function getElementFootnotesLetters(uid) {
  let footnotesLetters = ''
  footnotesStore.studyFootnotes.forEach((footnote) => {
    footnote.referenced_items.forEach((item) => {
      if (item.item_uid === uid) {
        footnotesLetters += dataFormating.footnoteSymbol(footnote.order)
      } else if (
        uid &&
        typeof uid !== 'string' &&
        uid.includes(item.item_uid)
      ) {
        footnotesLetters += dataFormating.footnoteSymbol(footnote.order)
      }
    })
  })
  return Array.from(new Set(footnotesLetters.split(''))).join(' ')
}

export default {
  getSoaRowClasses,
  getSoaRowType,
  getSoaFirstCellClasses,
  getElementFootnotesLetters,
}
