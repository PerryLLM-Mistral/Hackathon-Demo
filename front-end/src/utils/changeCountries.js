const changeCountryData = (countries, new_country) => {
    let country = countries.find((c) => c.id === new_country.id)
    country.demography = new_country.demography
    country.economy = new_country.economy
    country.military = new_country.military
    country.social = new_country.social
    country.technology = new_country.technology

    return country
}

const changeValues = (countries, setCountries, new_country) => {
    if (!new_country?.social) return;
    
    const get_country_changed = changeCountryData(countries, new_country)

    setCountries(prevCountries => {
        const filtered = prevCountries.filter(
            (c) => c.id !== new_country.id
        )
        return [...filtered, get_country_changed]
    })
}

export default changeValues
