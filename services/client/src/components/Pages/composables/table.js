const getColumns = (data) => {
  if (!data) {
    return []
  }

  if (data.length === 0) {
    return []
  }

  const ret = Object.keys(data[0])
    .map((key) => {
      return {
        field: key,
        header: key,
        sortable: true
      }
    })
    .filter((col) => col.field !== 'id') // get all columns except id

  return ret
}

export { getColumns }
