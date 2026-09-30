/** @odoo-module **/
import * as searchDates from "@web/search/utils/dates";
import { QUARTERS } from "@web/search/utils/dates";

import { Domain } from "@web/core/domain";
import { serializeDate, serializeDateTime } from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";
import { clamp, range } from "@web/core/utils/numbers";
import { pick } from "@web/core/utils/objects";

// Same relative offsets as web's dates.js (they are not exported).
const START_MONTH = -2;
const END_MONTH = 0;
const START_YEAR = -2;
const END_YEAR = 0;

const isJalaali = () => odoo.user_calendar_type === "jalaali";

const originalGetPeriodOptions = searchDates.getPeriodOptions;
const originalGetSelectedOptions = searchDates.getSelectedOptions;
const originalGetSetParam = searchDates.getSetParam;
const originalConstructDateRange = searchDates.constructDateRange;
const originalConstructDateDomain = searchDates.constructDateDomain;

function joinWithYear(description, year) {
    return localization.direction === "rtl" ? `${year} ${description}` : `${description} ${year}`;
}

function getJalaaliMonthPeriodOptions(referenceMoment) {
    return range(START_MONTH, END_MONTH + 1)
        .map((months) => {
            const date = referenceMoment.plus({ jmonths: months });
            const yearOffset = date.jyear - referenceMoment.jyear;
            return {
                id: searchDates.toGeneratorId("month", months),
                defaultYearId: searchDates.toGeneratorId(
                    "year",
                    clamp(yearOffset, START_YEAR, END_YEAR)
                ),
                description: date.toFormat("jMMMM"),
                granularity: "jmonth",
                groupNumber: 1,
                plusParam: { jmonths: months },
            };
        })
        .reverse();
}

function getJalaaliQuarterPeriodOptions() {
    const defaultYearId = searchDates.toGeneratorId("year", 0);
    return Object.values(QUARTERS).map((quarter, index) => ({
        id: ["first_quarter", "second_quarter", "third_quarter", "fourth_quarter"][index],
        groupNumber: 1,
        description: quarter.description,
        setParam: { jquarter: index + 1 },
        granularity: "jquarter",
        defaultYearId,
    }));
}

function getJalaaliYearPeriodOptions(referenceMoment) {
    return range(START_YEAR, END_YEAR + 1)
        .map((years) => {
            const date = referenceMoment.plus({ jyears: years });
            return {
                id: searchDates.toGeneratorId("year", years),
                description: date.toFormat("jyyyy"),
                granularity: "jyear",
                groupNumber: 2,
                plusParam: { jyears: years },
            };
        })
        .reverse();
}

function getCustomPeriodOptions(optionsParams) {
    const { customOptions } = optionsParams;
    return customOptions.map((option) => ({
        id: option.id,
        description: option.description,
        granularity: "withDomain",
        groupNumber: 3,
        domain: option.domain,
    }));
}

searchDates.getPeriodOptions = function (referenceMoment, optionsParams) {
    if (!isJalaali()) {
        return originalGetPeriodOptions(referenceMoment, optionsParams);
    }
    return [
        ...getJalaaliMonthPeriodOptions(referenceMoment),
        ...getJalaaliQuarterPeriodOptions(),
        ...getJalaaliYearPeriodOptions(referenceMoment),
        ...getCustomPeriodOptions(optionsParams),
    ];
};

searchDates.getSetParam = function (periodOption, referenceMoment) {
    if (!isJalaali()) {
        return originalGetSetParam(periodOption, referenceMoment);
    }
    if (periodOption.granularity === "jquarter") {
        return periodOption.setParam;
    }
    const date = referenceMoment.plus(periodOption.plusParam);
    const granularity = periodOption.granularity;
    return { [granularity]: date[granularity] };
};

searchDates.getSelectedOptions = function (referenceMoment, searchItem, selectedOptionIds) {
    if (!isJalaali()) {
        return originalGetSelectedOptions(referenceMoment, searchItem, selectedOptionIds);
    }
    const selectedOptions = { jyear: [] };
    const periodOptions = searchDates.getPeriodOptions(referenceMoment, searchItem.optionsParams);
    for (const optionId of selectedOptionIds) {
        const option = periodOptions.find((option) => option.id === optionId);
        const granularity = option.granularity;
        if (!selectedOptions[granularity]) {
            selectedOptions[granularity] = [];
        }
        if (option.domain) {
            selectedOptions[granularity].push(pick(option, "domain", "description"));
        } else {
            const setParam = searchDates.getSetParam(option, referenceMoment);
            selectedOptions[granularity].push({ granularity, setParam });
        }
    }
    return selectedOptions;
};

searchDates.constructDateRange = function (params) {
    if (!isJalaali()) {
        return originalConstructDateRange(params);
    }
    const { referenceMoment, fieldName, fieldType, granularity, setParam, plusParam } = params;
    if ("jquarter" in setParam) {
        // Luxon does not consider quarter key in setParam (like moment did)
        setParam.jmonth = QUARTERS[setParam.jquarter].coveredMonths[0];
        delete setParam.jquarter;
    }
    const date = referenceMoment.set(setParam).plus(plusParam || {});
    const leftDate = date.startOf(granularity);
    const rightDate = date.endOf(granularity);
    const leftBound = fieldType === "date" ? serializeDate(leftDate) : serializeDateTime(leftDate);
    const rightBound =
        fieldType === "date" ? serializeDate(rightDate) : serializeDateTime(rightDate);
    const domain = new Domain(["&", [fieldName, ">=", leftBound], [fieldName, "<=", rightBound]]);

    const year = date.toFormat("jyyyy");
    let description = year;
    if (granularity === "jmonth") {
        description = joinWithYear(date.toFormat("jMMMM"), year);
    } else if (granularity === "jquarter") {
        description = joinWithYear(QUARTERS[date.jquarter].description.toString(), year);
    }
    return { domain, description };
};

searchDates.constructDateDomain = function (referenceMoment, searchItem, selectedOptionIds) {
    if (!isJalaali()) {
        return originalConstructDateDomain(referenceMoment, searchItem, selectedOptionIds);
    }
    const selectedOptions = searchDates.getSelectedOptions(
        referenceMoment,
        searchItem,
        selectedOptionIds
    );
    if ("withDomain" in selectedOptions) {
        return {
            description: selectedOptions.withDomain[0].description,
            domain: Domain.and([selectedOptions.withDomain[0].domain, searchItem.domain]),
        };
    }
    const yearOptions = selectedOptions.jyear;
    const otherOptions = [...(selectedOptions.jquarter || []), ...(selectedOptions.jmonth || [])];
    searchDates.sortPeriodOptions(yearOptions);
    searchDates.sortPeriodOptions(otherOptions);
    const ranges = [];
    const { fieldName, fieldType } = searchItem;
    for (const yearOption of yearOptions) {
        const constructRangeParams = { referenceMoment, fieldName, fieldType };
        if (otherOptions.length) {
            for (const option of otherOptions) {
                const setParam = Object.assign({}, yearOption.setParam, option.setParam || {});
                const { granularity } = option;
                ranges.push(
                    searchDates.constructDateRange(
                        Object.assign({ granularity, setParam }, constructRangeParams)
                    )
                );
            }
        } else {
            const { granularity, setParam } = yearOption;
            ranges.push(
                searchDates.constructDateRange(
                    Object.assign({ granularity, setParam }, constructRangeParams)
                )
            );
        }
    }
    let domain = Domain.combine(
        ranges.map((range) => range.domain),
        "OR"
    );
    domain = Domain.and([domain, searchItem.domain]);
    const description = ranges.map((range) => range.description).join("/");
    return { domain, description };
};
