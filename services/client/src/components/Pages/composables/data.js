const list2Dict = (rawData, nameColumn) => {
  // Transform rawData of form Array[{SCENARIO, nameColumn, YEAR, ...}]
  // to data of form Object{nameColumn: Array[{SCENARIO, YEAR, ...}]}
  const names = [
    ...new Set(
      rawData.map((item) => {
        return item[nameColumn]
      })
    )
  ]

  const data = names.reduce((acc, com) => {
    acc[com] = rawData.filter((item) => item[nameColumn] == com)
    return acc
  }, {})

  return { data, names }
}

export { list2Dict }
